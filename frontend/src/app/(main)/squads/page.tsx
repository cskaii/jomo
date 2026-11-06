import { redirect } from "next/navigation";

export default function SquadsPage() {
  redirect("/garden?groups=1#garden-groups");
}
