"use client";

import { useEffect, useState } from "react";
import { getErrorPopupEventName, type ErrorPopupDetail } from "@/lib/error-popup";

export function ErrorModalHost() {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("Something went wrong");
  const [message, setMessage] = useState("");
  const [variant, setVariant] = useState<"error" | "success">("error");

  useEffect(() => {
    const handler = (event: Event) => {
      const custom = event as CustomEvent<ErrorPopupDetail>;
      const detail = custom.detail;
      if (!detail?.message) return;
      setTitle(detail.title || "Something went wrong");
      setMessage(detail.message);
      setVariant(detail.variant || "error");
      setOpen(true);
    };

    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };

    window.addEventListener(getErrorPopupEventName(), handler as EventListener);
    window.addEventListener("keydown", esc);
    return () => {
      window.removeEventListener(getErrorPopupEventName(), handler as EventListener);
      window.removeEventListener("keydown", esc);
    };
  }, []);

  if (!open) return null;

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" onClick={() => setOpen(false)}>
      <div className={`modal-card ${variant === "success" ? "success" : "error"}`} onClick={(e) => e.stopPropagation()}>
        <p className="eyebrow">Notice</p>
        <h3>{title}</h3>
        <p className="meta">{message}</p>
        <button type="button" onClick={() => setOpen(false)}>
          Close
        </button>
      </div>
    </div>
  );
}
