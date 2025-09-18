import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet"
import ChatBot from "./ChatBot"

interface AiPanelProps {
    open: boolean
    onOpenChange: (open: boolean) => void
}

export default function AiPanel({ open, onOpenChange }: AiPanelProps) {
    return <div>
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent> 
                <SheetHeader>
                    <SheetTitle>Ask your Query</SheetTitle>
                    <SheetDescription>
                        <ChatBot />
                    </SheetDescription>
                </SheetHeader>
            </SheetContent>
        </Sheet>
    </div>
}