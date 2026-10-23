"use client";

import { MotionConfig, motion, type HTMLMotionProps } from "framer-motion";
import type { ReactNode } from "react";

/** Honour the visitor's "reduce motion" setting everywhere */
export function MotionProvider({ children }: { children: ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}

/** Fades and lifts its content in the first time it scrolls into view */
export function Reveal({
  children,
  delay = 0,
  className,
  ...rest
}: { children: ReactNode; delay?: number } & HTMLMotionProps<"div">) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -10% 0px" }}
      transition={{ duration: 0.7, delay, ease: [0.2, 0.8, 0.2, 1] }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}
