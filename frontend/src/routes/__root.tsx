import { Outlet, createRootRoute } from "@tanstack/react-router"
import React, { Suspense } from "react"
import { Toaster } from "@/components/ui/sonner"

const loadDevtools = () =>
  Promise.all([
    import("@tanstack/router-devtools"),
    import("@tanstack/react-query-devtools"),
  ]).then(([routerDevtools, reactQueryDevtools]) => {
    return {
      default: () => (
        <>
          <routerDevtools.TanStackRouterDevtools />
          <reactQueryDevtools.ReactQueryDevtools />
        </>
      ),
    }
  })

const TanStackDevtools =
  process.env.NODE_ENV === "production" ? () => null : React.lazy(loadDevtools)

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <Toaster />
      <Suspense>
        <TanStackDevtools />
      </Suspense>
    </>
  ),
})
