import { notFound } from "next/navigation";
import StudyKitHome from "../../../../components/study/StudyKitHome";

export default async function StudyKitPage({
  params,
}: {
  params: Promise<{ kitId: string }>;
}) {
  const { kitId } = await params;
  const id = Number(kitId);
  if (!Number.isInteger(id) || id <= 0) notFound();

  return <StudyKitHome kitId={id} />;
}
