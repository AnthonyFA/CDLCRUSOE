export const comparator_config = {
  max_distance: 3,                 
  path: {
    apply: true,
    subnet: 1.75,                 
    organization_unit: 1.25,
    contact: 1.15,
  },
  comparators: {
    os: {
      apply: true,
      critical_bound: 0.35,        
      diff_value: 0.15,           
      vendor: 0.65, product: 0.30, version: 0.15,   
    },
    antivirus: {
      apply: true,
      critical_bound: 0.60,       
      diff_value: 0.30,           
      vendor: 0.50, product: 0.30, version: 0.20,
    },
    cms: {
      apply: true,
      require_open_ports: true,   
      critical_bound: 0.50,        
      diff_value: 0.30,
      vendor: 0.60, product: 0.30, version: 0.10,
    },
    net_service: {
      apply: true,
      critical_bound: 0.30,        
      diff_value: 0.10,
    },
    cve_cumulative: {
      apply: false,
      critical_bound: 0.55,        
    },
    event_cumulative: {
      apply: false,
      critical_bound: 0.02,       
  },
 },
};