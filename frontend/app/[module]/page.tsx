import { notFound, redirect } from "next/navigation";

import { legacyModuleTarget } from "@/lib/navigation";


export default async function LegacyModulePage({
  params,
}: {
  params: Promise<{ module: string }>;
}) {
  const { module } = await params;
  const target = legacyModuleTarget(module);
  if (!target) notFound();
  redirect(target);
}
