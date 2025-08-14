import { Button } from "@/components/ui/button"
import { createFileRoute } from "@tanstack/react-router"
import Categories from "@/components/Categories"
import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser, logout } = useAuth()

  const handleLogout = async () => {
    logout()
  }

  return (
    <>
      <div className="w-full">
        <div className="pt-12 m-4">
          <p className="text-2xl max-w-sm">
            Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
          </p>
          <p>Welcome back, nice to see you again!</p>
          <Button onClick={handleLogout}>LogOut</Button>
        </div>
        <Categories/>
      </div>
    </>
  )
}
