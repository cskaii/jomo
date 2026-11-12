// Real PostgreSQL/PLpgSQL checks in PGlite's disposable WASM database.
// Install test-only runtime: npm install --prefix frontend/.next-prototype-qa @electric-sql/pglite
// Run from repository root: node scripts/verify-postgres-schema.cjs
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const root = path.resolve(__dirname, '..');
const { PGlite } = require(path.join(root, 'frontend/.next-prototype-qa/node_modules/@electric-sql/pglite'));

async function main() {
  const db = new PGlite();
  try {
    await db.exec('CREATE ROLE anon; CREATE ROLE authenticated; CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY);');
    const schema = fs.readFileSync(path.join(root, 'supabase/schema.sql'), 'utf8');
    const fresh = new PGlite();
    try {
      await fresh.exec('CREATE ROLE anon; CREATE ROLE authenticated; CREATE SCHEMA auth; CREATE TABLE auth.users(id uuid PRIMARY KEY);');
      await fresh.exec(schema);
      const tables = (await fresh.query("SELECT count(*) AS n FROM pg_tables WHERE schemaname='public'")).rows[0];
      assert.equal(Number(tables.n), 34);
      assert.equal(Number((await fresh.query("SELECT count(*) AS n FROM pg_tables WHERE schemaname='public' AND rowsecurity")).rows[0].n), 34);
      assert.equal((await fresh.query('SELECT version_num FROM public.alembic_version')).rows[0].version_num, 'e21b9d73a401');
      console.log('PASS: Full fresh schema creates 33 application tables plus bookkeeping, with RLS, at the daily-activity revision.');
    } finally { await fresh.close(); }
    const marker = schema.indexOf('-- Running upgrade c8e31a04d912 -> d91e7c20b403');
    assert.ok(marker > 0);
    await db.exec(schema.slice(0, marker) + '\nCOMMIT;');
    const upgrade = fs.readFileSync(path.join(root, 'supabase/prototype_upgrade.sql'), 'utf8');
    await db.exec(upgrade);
    await db.exec(upgrade);
    assert.equal((await db.query('SELECT version_num FROM public.alembic_version')).rows[0].version_num, 'd91e7c20b403');
    console.log('PASS: PostgreSQL migration and idempotent SQL Editor upgrade execute successfully.');
    const insert = async (table, values) => {
      const keys = Object.keys(values);
      await db.query(`INSERT INTO ${table} (${keys.join(',')}) VALUES (${keys.map((_, i) => '$' + (i + 1)).join(',')})`, Object.values(values));
    };
    const now = new Date().toISOString(), owner = randomUUID(), member = randomUUID(), group = randomUUID();
    for (const id of [owner, member]) {
      await insert('auth.users', { id });
      await insert('public.users', { id, username: 'u_' + id.slice(0, 8), display_name: 'Test user', created_at: now, updated_at: now });
    }
    await insert('public.groups', { id: group, name: 'Shared', created_by: owner, visibility: 'invite_only', created_at: now, updated_at: now });
    for (const id of [owner, member]) await insert('public.group_members', { group_id: group, user_id: id, role: id === owner ? 'owner' : 'member', status: 'active', joined_at: now });
    const garden = randomUUID(), personal = randomUUID(), item = randomUUID(), activity = randomUUID(), participant = randomUUID(), proof = randomUUID();
    await insert('public.gardens', { id: garden, garden_type: 'group', owner_group_id: group, name: 'Shared', points_balance: 75, growth_level: 1, created_at: now, updated_at: now });
    await insert('public.gardens', { id: personal, garden_type: 'personal', owner_user_id: owner, name: 'Personal', points_balance: 50, growth_level: 1, created_at: now, updated_at: now });
    await insert('public.garden_catalog_items', { id: item, name: 'Plant', description: 'Test', item_type: 'seed', price_points: 25, asset_key: 'test', is_active: true, created_at: now });
    await insert('public.garden_items', { id: randomUUID(), garden_id: garden, catalog_item_id: item, quantity: 1, created_at: now });
    await insert('public.activities', { id: activity, created_by: owner, group_id: group, title: 'Walk', description: '', category: 'walk', visibility: 'group', status: 'awaiting_proof', duration_minutes: 10, max_participants: 10, location_required: false, proof_requirement: 'photo', max_reward_points: 10, created_at: now, updated_at: now });
    await insert('public.activity_participants', { id: participant, activity_id: activity, user_id: owner, status: 'awaiting_proof', joined_at: now, eligible_minutes: 10, points_awarded: 0 });
    await insert('public.point_transactions', { id: randomUUID(), garden_id: garden, user_id: owner, activity_participant_id: participant, transaction_type: 'spend', amount: -25, reason: 'Private activity description', idempotency_key: 'private:' + owner, created_at: now });
    const key = 'proofs/' + randomUUID().replaceAll('-', '') + '.jpg';
    await insert('public.proof_submissions', { id: proof, activity_id: activity, participant_id: participant, proof_type: 'photo', storage_key: key, status: 'pending', submitted_at: now });
    await db.exec('BEGIN;');
    await db.query('DELETE FROM auth.users WHERE id=$1', [owner]);
    assert.equal(Number((await db.query('SELECT count(*) AS n FROM public.storage_deletions')).rows[0].n), 1);
    await db.exec('ROLLBACK;');
    assert.equal(Number((await db.query('SELECT count(*) AS n FROM auth.users WHERE id=$1', [owner])).rows[0].n), 1);
    assert.equal(Number((await db.query('SELECT count(*) AS n FROM public.storage_deletions')).rows[0].n), 0);
    console.log('PASS: Auth, app-account and queued-photo deletion roll back atomically.');
    await db.query('DELETE FROM auth.users WHERE id=$1', [owner]);
    assert.equal(Number((await db.query('SELECT count(*) AS n FROM public.users WHERE id=$1', [owner])).rows[0].n), 0);
    assert.equal((await db.query('SELECT created_by FROM public.groups WHERE id=$1', [group])).rows[0].created_by, member);
    assert.equal((await db.query('SELECT role FROM public.group_members WHERE group_id=$1 AND user_id=$2', [group, member])).rows[0].role, 'owner');
    assert.equal((await db.query('SELECT points_balance FROM public.gardens WHERE id=$1', [garden])).rows[0].points_balance, 75);
    assert.equal(Number((await db.query('SELECT count(*) AS n FROM public.garden_items WHERE garden_id=$1', [garden])).rows[0].n), 1);
    const ledger = (await db.query('SELECT user_id, activity_participant_id, reason, idempotency_key FROM public.point_transactions WHERE garden_id=$1', [garden])).rows[0];
    assert.equal(ledger.user_id, null); assert.equal(ledger.activity_participant_id, null);
    assert.equal(ledger.reason, 'Former member transaction'); assert.ok(!ledger.idempotency_key.includes(owner));
    assert.equal((await db.query('SELECT storage_key FROM public.storage_deletions')).rows[0].storage_key, key);
    await assert.rejects(insert('public.users', { id: owner, username: 'stale', display_name: 'Stale request', created_at: now, updated_at: now }));
    console.log('PASS: Owner deletion transfers group ownership, preserves shared assets/balance, anonymises ledger and queues the private photo.');
    console.log('PASS: Deleted Auth identity cannot be recreated by an in-flight stale profile write.');
    await db.exec(`CREATE SCHEMA storage;
      CREATE TABLE storage.buckets(id text PRIMARY KEY, name text, public boolean, file_size_limit bigint, allowed_mime_types text[]);
      CREATE TABLE storage.objects(bucket_id text, name text); ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
      GRANT USAGE ON SCHEMA storage TO anon, authenticated; GRANT SELECT, INSERT ON storage.objects TO anon, authenticated;
      CREATE POLICY old_broad_policy ON storage.objects FOR ALL TO authenticated USING (true) WITH CHECK (true);
      INSERT INTO storage.objects VALUES ('activity-proofs','private.jpg'), ('another-bucket','allowed.jpg');`);
    const storage = fs.readFileSync(path.join(root, 'supabase/storage_setup.sql'), 'utf8');
    await db.exec(storage); await db.exec(storage);
    const bucket = (await db.query("SELECT public, file_size_limit FROM storage.buckets WHERE id='activity-proofs'")).rows[0];
    assert.equal(bucket.public, false); assert.equal(Number(bucket.file_size_limit), 2097152);
    await db.exec('SET ROLE authenticated;');
    const objects = (await db.query('SELECT * FROM storage.objects')).rows;
    assert.equal(objects.length, 1); assert.equal(objects[0].bucket_id, 'another-bucket');
    await assert.rejects(db.query("INSERT INTO storage.objects VALUES ('activity-proofs','forbidden.jpg')"));
    await db.exec('RESET ROLE;');
    console.log('PASS: Private bucket setup is idempotent and restrictive RLS blocks proof reads/writes despite an older broad policy.');
  } finally { await db.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
