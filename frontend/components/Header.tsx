import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="container mx-auto flex h-16 items-center px-4">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-primary">
            <span className="text-xl font-bold text-primary-foreground">A</span>
          </div>
          <span className="text-lg font-semibold">Agent Conversation</span>
        </Link>
      </div>
    </header>
  );
}
