'use client'

import UploadArea from "@/components/Dashboard/UploadArea";
import DocumentViewer from "@/components/Dashboard/DocumentViewer";
import SummaryPanel from "@/components/Dashboard/SummaryPanel";
import ChatBot from "@/components/Dashboard/ChatBot";
import { sampleSummary, veryLongText } from "@/assets/samples/texts/text";
import AiPanel from "@/components/Dashboard/AiPanel";
import { useState } from "react";

export default function DashboardPage() {
  // pretend state: doc uploaded or not
  const isUploaded = true; // replace with real state later
  const [openAiPanel, setOpenAiPanel] = useState(false)
  const [openSummaryPanel, setOpenSummaryPanel] = useState(false)

  return (
    <div className="container mx-auto flex gap-6 py-6 px-4">
      {!isUploaded ? (
        <UploadArea />
      ) : (
        <>
          <div className="flex-1">
            <DocumentViewer fileUrl="/contract.pdf" setOpenAiPanel={setOpenAiPanel} setOpenSummaryPanel={setOpenSummaryPanel} />
            <AiPanel open={openAiPanel} onOpenChange={setOpenAiPanel}/>
            <SummaryPanel summary={sampleSummary} open={openSummaryPanel} onOpenChange={setOpenSummaryPanel} />
          </div>
        </>
      )}
    </div>
  );
}
