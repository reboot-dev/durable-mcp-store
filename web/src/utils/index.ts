export const formatPrice = (priceCents?: bigint): string => {
  if (!priceCents) return "$0.00";
  const dollars = Number(priceCents) / 100;
  return `$${dollars.toFixed(2)}`;
};

export const sendPromptToParent = (prompt: string): void => {
  if (window.parent) {
    window.parent.postMessage(
      {
        type: "prompt",
        payload: {
          prompt,
        },
      },
      "*"
    );
  }
};
