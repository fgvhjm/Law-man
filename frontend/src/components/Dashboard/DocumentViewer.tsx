"use client";

import { useState } from "react";
import { DocumentViewerProps } from "@/types";
import { Button } from "../ui/button";

export default function DocumentViewer({ fileUrl }: DocumentViewerProps) {

  if (!fileUrl) {
    return (
      <div className="border rounded-lg p-4 h-[80vh] flex items-center justify-center text-slate-500">
        No document uploaded yet.
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-4 h-[80vh] overflow-y-auto">
    <div className="flex justify-between">
      <h1 className="text-2xl font-semibold mb-10 text-center">Document Viewer</h1>
      <Button size="md">ASK AI</Button>
    </div>
      <div className="h-500">
        <iframe className="w-full h-full" src={fileUrl}></iframe>
      </div>
    </div>
  );
}
