import { useForm, SubmitHandler } from "react-hook-form";
import useAuth, { isLoggedIn } from "@/hooks/useAuth";
import { Body_auth_login_acces_token as AccessToken } from "../client";
import {
    createFileRoute,
    redirect,
} from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const Route = createFileRoute("/login")({
    component: Login,
    beforeLoad: async () => {
        if (isLoggedIn()) {
            throw redirect({
                to: "/",
            });
        }
    },
});

function Login() {
    const { loginMutation, resetError } = useAuth();

    const {
        register,
        handleSubmit,
        formState: { isSubmitting },
    } = useForm<AccessToken>({
        mode: "onBlur",
        criteriaMode: "all",
        defaultValues: {
            username: "",
            password: "",
        },
    });

    const onSubmit: SubmitHandler<AccessToken> = async (data) => {
        if (isSubmitting) return;
        console.log("data",data)
        resetError();

        try {
            await loginMutation.mutateAsync(data);
        } catch {
            // error is handled by useAuth hook
        }
    };

    return (
        <div className="flex justify-center items-center min-h-screen p-4">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle className="text-center">Login</CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="username">Email</Label>
                            <Input
                                id="username"
                                type="email"
                                {...register("username")}
                                required
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                {...register("password")}
                                required
                            />
                        </div>
                        <Button
                            type="submit"
                            className="w-full"
                            disabled={loginMutation.isPending}
                        >
                            {loginMutation.isPending ? "Logging in..." : "Login"}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
