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
import type { AxiosError } from "axios";

// ----- OpenApi-ts Config -----
//needs to know how to resolve the async token to sync declaration on the client.setconfig
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const token = async () => {
    return localStorage.getItem("access_token") || "";
};
client.setConfig({
    //here we set the backend api url
    // if issues of code calling the client before its configured we can use the runtimeAPI url: https://heyapi.dev/openapi-ts/clients/axios#configuration
    baseURL: import.meta.env.VITE_API_URL,
    //This field is used for set a token used for auth
    auth: () => "<my_token>",
});
//This can be used if we are not using sdks for auth
/*
client.instance.interceptors.request.use((config) => {
  config.headers.set('Authorization', 'Bearer <my_token>'); 
  return config;
});
*/

// ----- Tanstack Query Config -----

const handleApiError = (error: unknown) => {
    // Narrow the error type to AxiosError
    if (isAxiosError(error)) {
        if (error.response) {
            const status = error.response?.status;
            if (status && [401, 403].includes(status)) {
                localStorage.removeItem("access_token");
                window.location.href = "/login";
            }
            console.log("HTTP error status:", error.response.status);
        } else if (error.request) {
            console.log("Network error (no response received):", error.message);
        } else {
            console.log("Axios error:", error.message);
        }
    } else {
        if (error instanceof Error) {
            console.log(
                "Non-Axios error:",
                error.name,
                error.message,
                error.stack
            );
        } else {
            console.log("Non-Axios error (unknown type):", error);
        }
    }
};

// Type guard for AxiosError
function isAxiosError(error: unknown): error is AxiosError {
    return (
        typeof error === "object" &&
        error !== null &&
        (error as AxiosError).isAxiosError === true
    );
}

const queryClient = new QueryClient({
    queryCache: new QueryCache({
        onError: handleApiError,
    }),
    mutationCache: new MutationCache({
        onError: handleApiError,
    }),
});
// ----- Tanstack Router Config -----

const router = createRouter({ routeTree });
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
