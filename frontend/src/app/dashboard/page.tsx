import UploadArea from "@/components/Dashboard/UploadArea";
import DocumentViewer from "@/components/Dashboard/DocumentViewer";
import SummaryPanel from "@/components/Dashboard/SummaryPanel";
import ChatBot from "@/components/Dashboard/ChatBot";
import { veryLongText } from "@/assets/samples/texts/text";

export default function DashboardPage() {
  // pretend state: doc uploaded or not
  const isUploaded = true; // replace with real state later

  return (
    <div className="container mx-auto flex gap-6 py-6 px-4">
      {!isUploaded ? (
        <UploadArea />
      ) : (
        <>
          <div className="flex-1">
            <DocumentViewer fileUrl="/contract.pdf" />
          </div>
        </>
      )}
    </div>
  );
}
