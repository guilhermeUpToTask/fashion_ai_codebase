import type { AxiosError } from "axios"
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const emailPattern = {
  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
  message: "Invalid email address",
}

export const namePattern = {
  value: /^[A-Za-z\s\u00C0-\u017F]{1,30}$/,
  message: "Invalid name",
}
export const handleApiError = (error: unknown) => {
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