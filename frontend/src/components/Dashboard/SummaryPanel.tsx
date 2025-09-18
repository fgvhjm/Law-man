import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet"

export interface SummaryPanelProps {
    summary: string
    open: boolean
    onOpenChange: (open: boolean) => void
}

export default function SummaryPanel({ summary, open, onOpenChange }: SummaryPanelProps) {
    return <div>
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent>
                <SheetHeader>
                    <SheetTitle>Summary</SheetTitle>
                    <SheetDescription>
                      {summary}
                    </SheetDescription>
                </SheetHeader>
            </SheetContent>
        </Sheet>
    </div>
}
