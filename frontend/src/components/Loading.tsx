import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingProps {
    message?: string;
    fullPage?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({ message = "Synchronizing data...", fullPage = false }) => {
    const content = (
        <div className="flex flex-col items-center justify-center gap-4 animate-in fade-in duration-500">
            <div className="relative">
                <Loader2 className="h-12 w-12 text-primary animate-spin" />
                <div className="absolute inset-0 h-12 w-12 rounded-full border-4 border-primary/20" />
            </div>
            <p className="text-sm font-bold text-primary animate-pulse tracking-widest uppercase">
                {message}
            </p>
        </div>
    );

    if (fullPage) {
        return (
            <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
                {content}
            </div>
        );
    }

    return (
        <div className="w-full py-20 flex items-center justify-center">
            {content}
        </div>
    );
};
