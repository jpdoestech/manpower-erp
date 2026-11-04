const paths: Record<string, string> = {
  dashboard: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  building:
    "M4 21V3h12v18 M16 9h4v12 M2 21h20 M8 7h4 M8 11h4 M8 15h4 M9 21v-3h3v3",
  branch: "M6 3v12a3 3 0 0 0 3 3h9 M6 9h12 M18 6l3 3-3 3 M18 15l3 3-3 3",
  users:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M22 21v-2a4 4 0 0 0-3-4 M17 3a4 4 0 0 1 0 8",
  document: "M14 2H5v20h14V7z M14 2v5h5 M8 12h8 M8 16h6",
  layout: "M3 3h18v18H3z M3 9h18 M9 9v12",
  book: "M12 5C9 3 5 3 2 4v16c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1v16",
  wallet: "M20 7V4H3v16h18V7H3 M16 11h5v5h-5z",
  chart: "M3 3v18h18 M7 17v-5 M12 17V7 M17 17V4",
  settings:
    "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M12 2v3 M12 19v3 M2 12h3 M19 12h3 M5 5l2 2 M17 17l2 2 M5 19l2-2 M17 7l2-2",
  search: "M21 21l-5-5 M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4",
  panel: "M3 4h18v16H3z M9 4v16 M14 9l-3 3 3 3",
  sun: "M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10 M12 1v2 M12 21v2 M1 12h2 M21 12h2 M4 4l2 2 M18 18l2 2 M4 20l2-2 M18 6l2-2",
  arrow: "M5 12h14 M14 7l5 5-5 5",
};
export function Icon({ name }: { name: string }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name] ?? paths.document} />
    </svg>
  );
}
