import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { client } from "@/client/client.gen";
import {
    MutationCache,
    QueryCache,
    QueryClient,
    QueryClientProvider,
} from "@tanstack/react-query";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { routeTree } from "@/routeTree.gen";
import { handleApiError } from "./lib/utils";

// ----- OpenApi-ts Config -----
client.setConfig({
    //here we set the backend api url
    // if issues of code calling the client before its configured we can use the runtimeAPI url: https://heyapi.dev/openapi-ts/clients/axios#configuration
    baseURL: import.meta.env.VITE_API_URL,
    //This field is used for set a token used for auth
    auth: () => localStorage.getItem("access_token") ?? "",
});

// ----- Tanstack Query Config -----
const queryClient = new QueryClient({
    queryCache: new QueryCache({
        onError: handleApiError,
    }),
    mutationCache: new MutationCache({
        onError: handleApiError,
    }),
});
// ----- Tanstack Router Config -----

export const router = createRouter({
    routeTree,
    scrollRestoration: true,
});
declare module "@tanstack/react-router" {
    interface Register {
        router: typeof router;
    }
}

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <QueryClientProvider client={queryClient}>
            <RouterProvider router={router} />
        </QueryClientProvider>
    </StrictMode>
);
