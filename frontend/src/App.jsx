/**
 * App.jsx — Root application component
 * Mounts the router. All layout/page logic lives in the route tree.
 */

import { RouterProvider } from "react-router-dom";
import router from "./router";

export default function App() {
  return <RouterProvider router={router} />;
}
