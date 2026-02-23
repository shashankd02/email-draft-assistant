"use client";

import { createPortal } from "react-dom";

type FullscreenLoaderProps = {
  open: boolean;
  title: string;
  subtitle?: string;
  onCancel?: () => void;
  cancelLabel?: string;
};

export function FullscreenLoader({ open, title, subtitle, onCancel, cancelLabel = "Cancel" }: FullscreenLoaderProps) {
  if (!open || typeof document === "undefined") return null;
  return createPortal(
    <div className="thinking-overlay" aria-live="polite">
      <div className="thinking-card">
        <p className="thinking-title">{title}</p>
        {subtitle ? <p className="meta">{subtitle}</p> : null}
        <div className="thinking-bubbles" aria-hidden>
          <span />
          <span />
          <span />
        </div>
        {onCancel ? (
          <button type="button" className="thinking-cancel-btn" onClick={onCancel}>
            {cancelLabel}
          </button>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}
