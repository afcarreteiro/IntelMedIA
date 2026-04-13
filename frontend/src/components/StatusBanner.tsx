export function StatusBanner({ status }: { status: "IDLE" | "ACTIVE" | "CLOSED" }) {
  return <p>{`Session ${status}`}</p>;
}
