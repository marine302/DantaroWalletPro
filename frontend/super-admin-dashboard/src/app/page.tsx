import { BasePage } from "@/components/ui/BasePage";
import DashboardPage from "@/components/dashboard/DashboardPage";

export default function Home() {
  return (
    <BasePage title="대시보드" description="슈퍼 어드민 대시보드 메인 페이지">
      <DashboardPage />
    </BasePage>
  );
}
