import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors font-mono",
  {
    variants: {
      variant: {
        default: "border-waf-teal/30 bg-waf-teal/10 text-waf-teal",
        block: "border-waf-coral/30 bg-waf-coral/10 text-waf-coral",
        shadow: "border-waf-amber/30 bg-waf-amber/10 text-waf-amber",
        outline: "border-waf-border-strong bg-transparent text-waf-text-secondary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
