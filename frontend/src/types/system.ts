export type SystemModule = {
  name: string;
  enabled: boolean;
  implemented: boolean;
  loaded: boolean;
  error: string | null;
};
