'use client'

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";


export interface NavbarProps {
    websiteName: string
}

export default function Navbar({ websiteName }: NavbarProps) {
  const pathname = usePathname()

  return (
    <header className="border-b">
      <div className="container mx-auto flex justify-between items-center py-4 px-6">
        <Link href="/" className="text-xl font-bold text-slate-900">
          {websiteName}
        </Link>
        <div className="flex gap-3">
          {pathname === '/dashboard' ? (
            <Button variant="outline">Logout</Button>
          ) : (
            <>
              <Link href="/login">
                <Button variant="outline">Login</Button>
              </Link>
              <Link href="/register">
                <Button>Register</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
