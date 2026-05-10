"use client";

import { useEffect } from "react";

export function HomeBodyClass() {
  useEffect(() => {
    document.body.classList.add("homepage-active");

    return () => {
      document.body.classList.remove("homepage-active");
    };
  }, []);

  return null;
}
