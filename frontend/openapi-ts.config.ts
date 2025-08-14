import { defineConfig } from "@hey-api/openapi-ts"
//This is a updated config for openapi-ts, we need to install biome later
//We can test later to use the tanstack query plugin
export default defineConfig({
  //we can set this later to point to the backend source file
  input: "./openapi.json",
  output: {
    lint: 'eslint',
    // lint: 'biome'
    //format: 'biome'
    path: 'src/client',
  },
  plugins: ['@hey-api/client-axios']
  //needs to read the docs to achive the same pattern on the axios client sdk, to achive a cleaner method names in the generated SDK
  /*
      {
      name: "@hey-api/sdk",
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      operationId: true,
      methodNameBuilder: (operation) => {
        // @ts-ignore
        let name: string = operation.name
        // @ts-ignore
        let service: string = operation.service

        if (service && name.toLowerCase().startsWith(service.toLowerCase())) {
          name = name.slice(service.length)
        }

        return name.charAt(0).toLowerCase() + name.slice(1)
      },
    },
  */
})
