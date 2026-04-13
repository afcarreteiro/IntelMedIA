export function SoapPane({
  disabled,
  soap,
  onExport,
}: {
  disabled?: boolean;
  soap: string;
  onExport: () => Promise<void>;
}) {
  return (
    <section>
      <button type="button" onClick={() => void onExport()} disabled={disabled}>
        Export SOAP
      </button>
      {soap ? <pre>{soap}</pre> : null}
    </section>
  );
}
