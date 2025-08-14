import { Outlet, createRootRoute } from "@tanstack/react-router"
import { Toaster } from "@/components/ui/sonner"
import { CartProvider } from "@/lib/cart-context"

export const Route = createRootRoute({
  component: () => (
    <CartProvider>
      <Outlet />
      <Toaster />
    </CartProvider>
  ),
})
