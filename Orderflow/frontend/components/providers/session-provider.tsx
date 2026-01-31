'use client';

// Session bootstrap is now handled entirely by AuthProvider (JWT + stored user),
// so this provider becomes a simple passthrough to preserve the component tree.

export function SessionProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
