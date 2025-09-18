"use client";
import { useRef } from "react";
import { Button } from "@/components/ui/button";

export default function UploadArea() {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-12 w-full text-center">
      <p className="mb-4 text-slate-600">Upload your legal document to get started</p>
      <input ref={inputRef} type="file" accept=".pdf,.doc,.docx" className="hidden" />
      <Button onClick={() => inputRef.current?.click()}>Upload Document</Button>
    </div>
  );
}
