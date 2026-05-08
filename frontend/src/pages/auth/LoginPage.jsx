/**
 * LoginPage.jsx — Login page for CBC Learning Platform
 *
 * Form fields:
 *   - email (backend uses EMAIL as USERNAME_FIELD)
 *   - password
 *
 * On success: redirects to role-based dashboard via useAuth hook.
 */

import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../../hooks/useAuth";
import { Input } from "../../components/ui/Input";
import { Button } from "../../components/ui/Button";
import { AlertBanner } from "../../components/ui/AlertBanner";

// ── Validation Schema ─────────────────────────────────────────────────────────
const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

// ── Component ─────────────────────────────────────────────────────────────────
export default function LoginPage() {
  const { login, loginLoading, loginError } = useAuth();

  const {
    register,
    handleSubmit,
    setFocus,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: "onTouched",
  });

  // Auto-focus email on mount
  useEffect(() => {
    setFocus("email");
  }, [setFocus]);

  const onSubmit = async (values) => {
    await login(values.email, values.password);
  };

  return (
    <div className="auth-form">
      {/* Header */}
      <div className="auth-form__header">
        <h2 className="auth-form__title">Welcome back</h2>
        <p className="auth-form__subtitle">Sign in to your CBC Learn account</p>
      </div>

      {/* Global error */}
      <AlertBanner message={loginError} type="error" className="auth-form__alert" />

      {/* Form */}
      <form
        className="auth-form__body"
        onSubmit={handleSubmit(onSubmit)}
        noValidate
        aria-label="Login form"
      >
        <Input
          id="login-email"
          label="Email address"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          required
          error={errors.email?.message}
          {...register("email")}
        />

        <Input
          id="login-password"
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          required
          error={errors.password?.message}
          {...register("password")}
        />

        <div className="auth-form__forgot">
          <Link to="/forgot-password" className="auth-link auth-link--sm">
            Forgot password?
          </Link>
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          isLoading={loginLoading}
          className="auth-form__submit"
        >
          Sign in
        </Button>
      </form>

      {/* Footer */}
      <p className="auth-form__footer">
        Don't have an account?{" "}
        <Link to="/register" className="auth-link">
          Create one
        </Link>
      </p>
    </div>
  );
}
