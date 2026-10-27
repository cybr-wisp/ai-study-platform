import Dashboard from "../../../components/study/Dashboard";
import { mockCourses } from "../../../components/study/mockCourses";

export default function DashboardPage() {
  return <Dashboard courses={mockCourses} />;
}
