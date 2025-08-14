import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";

import {
    Auth,
    type AuthLoginAccesTokenData,
    type AuthRegisterUserData,
    type BodyAuthLoginAccesToken,
    type UserPublic,
    Users,
} from "@/client";

const isLoggedIn = () => {
    return localStorage.getItem("access_token") !== null;
};

const useAuth = () => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();

    const { data: user, isLoading } = useQuery<UserPublic | null, Error>({
        queryKey: ["currentUser"],
        queryFn: async () => {
            const res = await Users.readUserMe();
            return res.data ?? null;
        },
        enabled: isLoggedIn(),
    });
    const signUpMutation = useMutation({
        mutationFn: (data: AuthRegisterUserData) => Auth.registerUser(data),

        onSuccess: () => {
            navigate({ to: "/login" });
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
        },
    });
    const loginMutation = useMutation({
        //Typo in the original code: 'loginAccesToken' should be 'loginAccessToken', needs to change in the backend endpoint and regenrate the client
        mutationFn: (data: BodyAuthLoginAccesToken) =>
            Auth.loginAccesToken({ body: data}),
        onSuccess: (res) => {
            if (res.data?.access_token) {
                localStorage.setItem("access_token", res.data?.access_token);
            }
            queryClient.invalidateQueries({ queryKey: ["currentUser"] });
            navigate({ to: "/" });
        },
    });
    const logout = () => {
        localStorage.removeItem("access_token");
        queryClient.setQueryData<UserPublic | null>(["currentUser"], null);
        queryClient.invalidateQueries({ queryKey: ["users"] });
        navigate({ to: "/login" });
    };

    return {
        signUpMutation,
        loginMutation,
        logout,
        user,
        isLoading,
    };
};

export { isLoggedIn };
export default useAuth;
