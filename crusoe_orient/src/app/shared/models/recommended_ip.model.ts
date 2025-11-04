export interface RecommendedIP extends AttackedIP {
  risk: number;
  distance: number;
  path_types: string[];
  warnings: RecommenderWarning[];
}

export interface NetworkService {
  service: string;
  port: number;
  protocol: string;
}

export interface RecommenderWarning {
  message: string;
  partial_similarity: number;
}

export interface AttackedIP {
  ip: string;
  domains: string[];
  contacts: string[];
  os: {
    vendor: string;
    product: string;
    version: string;
  };
  antivirus: null | {
    vendor: string;
    product: string;
    version: string;
  };
  cms: null | {
    vendor: string;
    product: string;
    version: string;
  };
  cve_count: number;
  security_event_count: number;
  network_services: NetworkService[];

  recommendations?: Recommendation[];
}

export interface Recommendation {
  title: string;
  severity: string;  
  rationale?: string;
  actions?: string[];
  refs?: RecommendationRef[];
}

export interface RecommendationRef {
  type: string;      
  id?: string;
  url?: string | null;
}