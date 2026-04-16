import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonVariant = "primary" | "secondary" | "danger";

const variantClassName: Record<ButtonVariant, string> = {
  primary: "bg-teal text-white hover:bg-teal/90 focus:ring-teal/30",
  secondary: "border border-line bg-panel text-ink hover:bg-surface focus:ring-blue/20",
  danger: "bg-red text-white hover:bg-red/90 focus:ring-red/25",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({ children, className = "", variant = "secondary", ...props }: PropsWithChildren<ButtonProps>) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition focus:outline-none focus:ring-4 disabled:cursor-not-allowed disabled:opacity-50 ${variantClassName[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
