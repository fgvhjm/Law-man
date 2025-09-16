"use client";

import { Dispatch, SetStateAction, useState } from "react";
import { Button } from "../ui/button";

export interface DocumentViewerProps {
    fileUrl: string
    setOpenAiPanel: Dispatch<SetStateAction<boolean>>
    setOpenSummaryPanel: Dispatch<SetStateAction<boolean>>
}

export default function DocumentViewer({ fileUrl, setOpenAiPanel, setOpenSummaryPanel }: DocumentViewerProps) {

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
        <div className="flex gap-2">
          <Button size="md" onClick={() => setOpenSummaryPanel(open => !open)} >View Summary</Button>
          <Button size="md" onClick={() => setOpenAiPanel(open => !open)}>Ask AI</Button>
        </div>
      </div>
      <div className="h-500">
        <iframe className="w-full h-full" src={fileUrl}></iframe>
      </div>
    </div>
  );
}
