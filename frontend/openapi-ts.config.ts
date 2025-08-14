import { defineConfig } from "@hey-api/openapi-ts";
//This is a updated config for openapi-ts, we need to install biome later
//We can test later to use the tanstack query plugin
export default defineConfig({
    //we can set this later to point to the backend source file
    input: "./openapi.json",
    output: {
        lint: "eslint",
        // lint: 'biome'
        //format: 'biome'
        path: "src/client",
    },

    plugins: [
        {
            name: "@hey-api/client-axios",
        },
        {
            name: "@hey-api/sdk",
            asClass: true,
            operationId: true,
            // Generates SDK method names from OpenAPI operations. Uses the operation's id as the base name, defaults to 'unnamedOperation' if missing, strips the first tag (service name) from the start to avoid redundancy, and converts the first character to lowercase for camelCase style.
            methodNameBuilder: (operation) => {
                let name: string = operation.id ?? "unnamedOperation";

                const service =
                    "tags" in operation ? operation.tags?.[0] ?? "" : "";

                if (
                    service &&
                    name.toLowerCase().startsWith(service.toLowerCase())
                ) {
                    name = name.slice(service.length);
                }

                return name.charAt(0).toLowerCase() + name.slice(1);
            },
        },
    ],
});
