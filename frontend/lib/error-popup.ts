export type ErrorPopupDetail = {
  message: string;
  title?: string;
  variant?: "error" | "success";
};

const EVENT_NAME = "app:error-popup";

function dispatchPopup(detail: ErrorPopupDetail): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<ErrorPopupDetail>(EVENT_NAME, { detail }));
}

export function showErrorPopup(message: string, title = "Something went wrong"): void {
  dispatchPopup({ message, title, variant: "error" });
}

export function showSuccessPopup(message: string, title = "Success"): void {
  dispatchPopup({ message, title, variant: "success" });
}

export function getErrorPopupEventName(): string {
  return EVENT_NAME;
}
