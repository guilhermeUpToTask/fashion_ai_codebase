# React + TypeScript + Shadcn UI Template

This is a feature-rich, opinionated starter template for building modern, scalable, and production-ready web applications. It comes pre-configured with a powerful stack of tools designed to maximize developer productivity and create a great user experience.



## ✨ Features

-   **Framework:** [React 19](https://react.dev/)
-   **Build Tool:** [Vite](https://vitejs.dev/) with SWC for blazing-fast development.
-   **Language:** [TypeScript](https://www.typescriptlang.org/) (with strict mode enabled).
-   **Styling:**
    -   [Tailwind CSS](https://tailwindcss.com/) v4 for utility-first styling.
    -   [Shadcn UI](https://ui.shadcn.com/) for a beautiful, accessible, and customizable component library.
    -   Dark mode support out-of-the-box.
-   **Routing:** [TanStack Router](https://tanstack.com/router) with type-safe, file-based routing.
-   **Data Fetching & State Management:** [TanStack Query](https://tanstack.com/query) for robust server-state management, caching, and background refetching.
-   **API Client:**
    -   [Axios](https://axios-http.com/) as the underlying HTTP client.
    -   [OpenAPI TS](https://heyapi.dev/openapi-ts) for automatic, type-safe client generation from an OpenAPI (Swagger) specification.
-   **Form Management:** [React Hook Form](https://react-hook-form.com/) for performant and flexible form handling.
-   **Authentication:** Pre-configured pattern for token-based authentication, including protected routes and automatic logout on 401/403 errors.
-   **Linting & Formatting:** A solid foundation with ESLint (Prettier/Biome can be easily added).
-   **Deployment:** Production-ready, multi-stage `Dockerfile` with Nginx for efficient and secure deployment.

## 🚀 Getting Started

### Prerequisites

-   [Node.js](https://nodejs.org/) (v20 or higher)
-   [Docker](https://www.docker.com/) (for containerized deployment)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/react-ts-tailwind-shadcn-template.git
    cd react-ts-tailwind-shadcn-template
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Set up environment variables:**
    Create a `.env.local` file in the root of the project by copying the example:
    ```bash
    cp .env.example .env.local
    ```
    Update the `VITE_API_URL` to point to your backend API endpoint.
    ```env
    # .env.local
    VITE_API_URL=http://localhost:8000/api
    ```

### Running the Development Server

To start the Vite development server with Hot Module Replacement (HMR):
```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

## 🏗️ Core Concepts

### 1. API Client Generation (OpenAPI TS)

This template uses `openapi-ts` to generate a fully typed API client from your backend's OpenAPI specification.

**Workflow:**
1.  Obtain an `openapi.json` file from your backend API (e.g., from `http://localhost:8000/openapi.json`).
2.  Place the `openapi.json` file in the root of the project.
3.  Run the generation script:
    ```bash
    npm run generate-client
    ```
4.  This will update the client located at `src/client/client.gen.ts`. You can now import and use the typed client throughout your application.

The client is pre-configured in `src/main.tsx` to use the `VITE_API_URL` and to include an authentication token from `localStorage`.

### 2. Authentication Flow

The template implements a standard token-based authentication pattern:
-   **Login:** The `login.tsx` page uses a custom `useAuth` hook to send credentials to the backend. Upon success, an access token is stored in `localStorage`.
-   **Protected Routes:** The `_layout.tsx` route acts as a guard. It uses a `beforeLoad` check to ensure a user is logged in before rendering any child routes. If not, it redirects to `/login`.
-   **Global Error Handling:** The TanStack Query client in `src/main.tsx` is configured to listen for `401 Unauthorized` or `403 Forbidden` errors. If one occurs, it automatically clears the token from `localStorage` and redirects the user to the login page.
-   **`useAuth` Hook:** You will need to implement the logic inside a `useAuth.ts` hook (a placeholder is assumed by the routes) to manage user state, login/logout mutations, and token handling.

### 3. Styling with Shadcn UI & Tailwind CSS

-   **Shadcn UI:** Components are added via the Shadcn CLI. They are not a dependency but rather code that you own and can modify in `src/components/ui`.
-   **Theming:** The theme is defined using CSS variables in `src/index.css`. You can easily customize colors, radii, and more by editing the `:root` and `.dark` blocks.
-   **Tailwind CSS:** All components are styled using Tailwind's utility classes, providing a consistent and maintainable design system.

### 4. Routing

Routing is managed by **TanStack Router**, which uses a file-based convention inside the `src/routes` directory.
-   `__root.tsx`: The main root layout. It includes providers and devtools.
-   `_layout.tsx`: A route segment with an underscore prefix (`_`) creates a layout route without adding to the URL path. This is used for protected routes.
-   `login.tsx`: A public route for authentication.
-   `/`: The index route for the authenticated part of the app.

The router is type-safe, meaning you get autocomplete and type-checking for paths, search params, and route loaders.

## 📜 Available Scripts

-   `npm run dev`: Starts the development server.
-   `npm run build`: Compiles and builds the application for production.
-   `npm run lint`: Lints the codebase using ESLint.
-   `npm run preview`: Serves the production build locally to preview it.
-   `npm run generate-client`: Generates the API client from `openapi.json`.

## 🐳 Deployment with Docker

This template includes a multi-stage `Dockerfile` for creating an optimized and secure production image.

**Build the Docker image:**
```bash
docker build -t my-react-app .

# To pass the API URL during the build:
docker build --build-arg VITE_API_URL=https://api.example.com/api -t my-react-app .
```

**Run the Docker container:**
```bash
docker run -d -p 8080:80 my-react-app
```
The application will be accessible at `http://localhost:8080`.

The `Dockerfile` uses a two-stage process:
1.  **`build-stage`:** Installs dependencies and builds the React application.
2.  **Final Stage:** Copies only the static build artifacts into a lightweight `nginx` image and serves them. This results in a small and secure final image.

## 🔧 Customization

1.  **Update `components.json`:** Modify aliases or base colors as needed.
2.  **Implement `useAuth.ts`:** Create your authentication hook to handle user state and API calls.
3.  **Customize Theme:** Adjust the CSS variables in `src/index.css` to match your brand.
4.  **Add a Formatter:** Choose and configure a code formatter like [Prettier](https://prettier.io/) or [Biome](https://biomejs.dev/) for consistent code style.
5.  **Expand ESLint:** Follow the instructions in `README.md` (the original one) to add more advanced, type-aware linting rules.

## 📄 License

This project is licensed under the MIT License.