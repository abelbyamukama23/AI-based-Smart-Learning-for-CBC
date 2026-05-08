/**
 * RegisterPage.jsx — Multi-step registration for CBC Learning Platform
 *
 * Step 1: Role Selection   (LEARNER | TEACHER)
 * Step 2: Personal Details (email, password, first_name, last_name)
 * Step 3: School Info      (Learner only — class_level, school_name, region, district)
 *
 * Maps exactly to backend RegisterSerializer fields.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "../../hooks/useAuth";
import { Input } from "../../components/ui/Input";
import { Select } from "../../components/ui/Select";
import { Button } from "../../components/ui/Button";
import { AlertBanner } from "../../components/ui/AlertBanner";

// ── Constants (mirror backend choices) ───────────────────────────────────────
const ROLES = {
  LEARNER: "LEARNER",
  TEACHER: "TEACHER",
};

const CLASS_LEVELS = ["S1", "S2", "S3", "S4", "S5", "S6"];

// ── Validation Schemas (per step) ─────────────────────────────────────────────
const personalSchema = z
  .object({
    first_name: z.string().min(1, "First name is required"),
    last_name: z.string().min(1, "Last name is required"),
    email: z.string().min(1, "Email is required").email("Invalid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain at least one uppercase letter")
      .regex(/[0-9]/, "Must contain at least one number"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

const schoolSchema = z.object({
  class_level: z.string().min(1, "Class level is required"),
  school_name: z.string().min(2, "School name is required"),
  region: z.string().min(2, "Region is required"),
  district: z.string().min(2, "District is required"),
});

// ── Step Indicator ────────────────────────────────────────────────────────────
function StepIndicator({ currentStep, totalSteps, role }) {
  const labels =
    role === ROLES.LEARNER
      ? ["Your Role", "Your Details", "School Info"]
      : ["Your Role", "Your Details"];
  const steps = role === ROLES.LEARNER ? 3 : 2;

  return (
    <div className="step-indicator" aria-label="Registration progress">
      {Array.from({ length: steps }).map((_, i) => (
        <div
          key={i}
          className={`step-indicator__item ${
            i + 1 === currentStep
              ? "step-indicator__item--active"
              : i + 1 < currentStep
              ? "step-indicator__item--done"
              : ""
          }`}
        >
          <div className="step-indicator__dot">
            {i + 1 < currentStep ? (
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path
                  d="M2 6l2.5 2.5L10 3"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : (
              <span>{i + 1}</span>
            )}
          </div>
          <span className="step-indicator__label">{labels[i]}</span>
          {i < steps - 1 && <div className="step-indicator__line" />}
        </div>
      ))}
    </div>
  );
}

// ── Step 1: Role Selection ────────────────────────────────────────────────────
function RoleStep({ selected, onSelect, onNext }) {
  return (
    <div className="auth-form__step">
      <div className="auth-form__header">
        <h2 className="auth-form__title">Who are you?</h2>
        <p className="auth-form__subtitle">
          Choose your role to personalise your experience.
        </p>
      </div>

      <div className="role-cards">
        <button
          type="button"
          id="role-learner"
          onClick={() => onSelect(ROLES.LEARNER)}
          className={`role-card ${selected === ROLES.LEARNER ? "role-card--selected" : ""}`}
          aria-pressed={selected === ROLES.LEARNER}
        >
          <span className="role-card__icon" aria-hidden>📚</span>
          <span className="role-card__title">Learner</span>
          <span className="role-card__desc">
            S1 – S6 student accessing CBC content and the AI tutor.
          </span>
        </button>

        <button
          type="button"
          id="role-teacher"
          onClick={() => onSelect(ROLES.TEACHER)}
          className={`role-card ${selected === ROLES.TEACHER ? "role-card--selected" : ""}`}
          aria-pressed={selected === ROLES.TEACHER}
        >
          <span className="role-card__icon" aria-hidden>🏫</span>
          <span className="role-card__title">Teacher</span>
          <span className="role-card__desc">
            Educator managing content and monitoring learner progress.
          </span>
        </button>
      </div>

      <Button
        variant="primary"
        size="lg"
        className="auth-form__submit"
        disabled={!selected}
        onClick={onNext}
      >
        Continue
      </Button>
    </div>
  );
}

// ── Step 2: Personal Details ──────────────────────────────────────────────────
function PersonalStep({ defaultValues, onNext, onBack }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(personalSchema),
    defaultValues,
    mode: "onTouched",
  });

  return (
    <div className="auth-form__step">
      <div className="auth-form__header">
        <h2 className="auth-form__title">Your details</h2>
        <p className="auth-form__subtitle">
          Fill in your personal information below.
        </p>
      </div>

      <form
        className="auth-form__body"
        onSubmit={handleSubmit(onNext)}
        noValidate
      >
        <div className="form-row">
          <Input
            id="reg-first-name"
            label="First name"
            placeholder="John"
            autoComplete="given-name"
            required
            error={errors.first_name?.message}
            {...register("first_name")}
          />
          <Input
            id="reg-last-name"
            label="Last name"
            placeholder="Doe"
            autoComplete="family-name"
            required
            error={errors.last_name?.message}
            {...register("last_name")}
          />
        </div>

        <Input
          id="reg-email"
          label="Email address"
          type="email"
          placeholder="you@example.com"
          autoComplete="email"
          required
          error={errors.email?.message}
          {...register("email")}
        />

        <Input
          id="reg-password"
          label="Password"
          type="password"
          placeholder="At least 8 characters"
          autoComplete="new-password"
          required
          error={errors.password?.message}
          helperText="Min. 8 characters, one uppercase, one number."
          {...register("password")}
        />

        <Input
          id="reg-confirm-password"
          label="Confirm password"
          type="password"
          placeholder="Repeat your password"
          autoComplete="new-password"
          required
          error={errors.confirm_password?.message}
          {...register("confirm_password")}
        />

        <div className="auth-form__nav">
          <Button type="button" variant="ghost" size="md" onClick={onBack}>
            ← Back
          </Button>
          <Button type="submit" variant="primary" size="lg">
            Continue
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── Step 3: School Info (Learner only) ────────────────────────────────────────
function SchoolStep({ defaultValues, onSubmit, onBack, isLoading, error }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schoolSchema),
    defaultValues,
    mode: "onTouched",
  });

  return (
    <div className="auth-form__step">
      <div className="auth-form__header">
        <h2 className="auth-form__title">Your school</h2>
        <p className="auth-form__subtitle">
          Help us connect you to the right CBC curriculum resources.
        </p>
      </div>

      <AlertBanner message={error} type="error" className="auth-form__alert" />

      <form
        className="auth-form__body"
        onSubmit={handleSubmit(onSubmit)}
        noValidate
      >
        <Select
          id="reg-class-level"
          label="Class level"
          required
          error={errors.class_level?.message}
          {...register("class_level")}
        >
          <option value="">Select your class</option>
          {CLASS_LEVELS.map((lvl) => (
            <option key={lvl} value={lvl}>
              {lvl}
            </option>
          ))}
        </Select>

        <Input
          id="reg-school-name"
          label="School name"
          placeholder="e.g. Kampala Secondary School"
          required
          error={errors.school_name?.message}
          {...register("school_name")}
        />

        <div className="form-row">
          <Input
            id="reg-region"
            label="Region"
            placeholder="e.g. Central"
            required
            error={errors.region?.message}
            {...register("region")}
          />
          <Input
            id="reg-district"
            label="District"
            placeholder="e.g. Kampala"
            required
            error={errors.district?.message}
            {...register("district")}
          />
        </div>

        <div className="auth-form__nav">
          <Button type="button" variant="ghost" size="md" onClick={onBack}>
            ← Back
          </Button>
          <Button
            type="submit"
            variant="primary"
            size="lg"
            isLoading={isLoading}
          >
            Create account
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── RegisterPage (Orchestrator) ───────────────────────────────────────────────
export default function RegisterPage() {
  const { register: doRegister, registerLoading, registerError } = useAuth();

  const [step, setStep] = useState(1);
  const [role, setRole] = useState(ROLES.LEARNER);

  // Accumulated data across steps
  const [formData, setFormData] = useState({});

  const totalSteps = role === ROLES.LEARNER ? 3 : 2;

  // Step 1 → 2
  const handleRoleNext = () => setStep(2);

  // Step 2 → 3 (or submit for TEACHER)
  const handlePersonalNext = async (values) => {
    const merged = { ...formData, ...values, role };
    setFormData(merged);
    if (role === ROLES.TEACHER) {
      await doRegister(merged);
    } else {
      setStep(3);
    }
  };

  // Step 3 → submit (LEARNER)
  const handleSchoolSubmit = async (values) => {
    const merged = { ...formData, ...values };
    await doRegister(merged);
  };

  return (
    <div className="auth-form">
      <StepIndicator currentStep={step} totalSteps={totalSteps} role={role} />

      {step === 1 && (
        <RoleStep
          selected={role}
          onSelect={setRole}
          onNext={handleRoleNext}
        />
      )}

      {step === 2 && (
        <PersonalStep
          defaultValues={formData}
          onNext={handlePersonalNext}
          onBack={() => setStep(1)}
        />
      )}

      {step === 3 && role === ROLES.LEARNER && (
        <SchoolStep
          defaultValues={formData}
          onSubmit={handleSchoolSubmit}
          onBack={() => setStep(2)}
          isLoading={registerLoading}
          error={registerError}
        />
      )}

      {step === 1 && (
        <p className="auth-form__footer">
          Already have an account?{" "}
          <Link to="/login" className="auth-link">
            Sign in
          </Link>
        </p>
      )}
    </div>
  );
}
