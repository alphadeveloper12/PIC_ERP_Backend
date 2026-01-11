import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function TaskCardSkeleton() {
    return (
        <Card className="border-primary/5 shadow-md overflow-hidden bg-white/50 backdrop-blur-sm animate-in fade-in duration-500">
            <CardContent className="p-0">
                <div className="flex items-center gap-6 p-6">
                    {/* Action icon placeholder */}
                    <Skeleton className="h-12 w-12 rounded-2xl flex-shrink-0" />

                    <div className="flex-1 min-w-0 space-y-3">
                        <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                                {/* Project Badge */}
                                <Skeleton className="h-4 w-24 mb-2 rounded-full" />
                                {/* Title */}
                                <Skeleton className="h-6 w-3/4 rounded-lg" />
                            </div>
                            {/* Status Badge */}
                            <Skeleton className="h-6 w-20 rounded-full" />
                        </div>

                        <div className="flex flex-wrap items-center gap-4">
                            {/* Info chips */}
                            <Skeleton className="h-4 w-32 rounded-lg" />
                            <Skeleton className="h-4 w-40 rounded-lg" />
                            <Skeleton className="h-4 w-24 rounded-lg" />
                        </div>
                    </div>

                    {/* Expand icon */}
                    <Skeleton className="h-5 w-5 rounded-full" />
                </div>
            </CardContent>
        </Card>
    );
}
