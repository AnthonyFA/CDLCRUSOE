import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { GraphInput } from 'src/app/shared/models/graph.model';
import { Node, Edge } from '@swimlane/ngx-graph';
import { environment } from 'src/environments/environment';
import { Observable, throwError } from 'rxjs';
import { AttackedIP, RecommendedIP } from '../models/recommended_ip.model';
import { switchMap, map, catchError } from 'rxjs/operators';
@Injectable({
  providedIn: 'root',
})
export class RecommenderService {
  private apiUrl = environment.recommenderApi;

  constructor(private http: HttpClient) {}

  getRecommendations(ip: string): Observable<GraphInput> {
    const rootUrl = `${this.apiUrl}recommender/attacked-host?ip=${ip}`;
    const recommendedUrl = `${this.apiUrl}recommender/recommended-hosts?ip=${ip}`;

return this.http.get<AttackedIP>(rootUrl).pipe(
  switchMap((initial_node) => {
    console.log('[✔️ initial_node]', initial_node);  // NUEVO

        return this.http.get<RecommendedIP[]>(recommendedUrl).pipe(
          map((data) => {
            console.log('[✔️ recommended data]', data);  // NUEVO

            const { nodes, edges } = this.convertToGraph(data, ip, initial_node);
            console.log('[✔️ final graph]', { nodes, edges });  // NUEVO

            return { nodes, edges };
          })
        );
      }),
      catchError((err) => {
        console.error('Error loading recommendations:', err);
        return throwError(() => err);
      })
      );
    }

  public convertToGraph(data: RecommendedIP[], root_ip: string, initial_node: AttackedIP): GraphInput {
    let nodes: Node[] = [];
    let edges: Edge[] = [];

    nodes.push(this.buildInitialNode(root_ip, initial_node));

    for (let i = 0; i < data.length; i++) {
      const current = data[i];
      const node_id = (i + 1).toString();
      nodes.push({
        id: node_id,
        label: current.ip,
        data: {
          ...this.sanitizeNodeData(current),
          customColor: 'red',
        },
      });


      edges.push({ source: '0', target: node_id, label: 'Same ' + current.path_types.join(', ') });
    }
    return { nodes, edges };
  }

  private sanitizeNodeData(data: any): any {
    const cleaned = { ...data };
    if (typeof cleaned.risk === 'number' && !Number.isFinite(cleaned.risk)) {
      cleaned.risk = 100;  // o null, o 'Max'
    }
    if (typeof cleaned.distance === 'number' && !Number.isFinite(cleaned.distance)) {
      cleaned.distance = -1;  // o null
    }
    return cleaned;
  }

  private buildInitialNode(root_ip: string, initial_node: AttackedIP): Node {
    let node: Node = {
      id: '0',
      label: root_ip,
      data: {
        customColor: 'green',
      },
    };

    if (!initial_node) return node;

    node.data = {
      ...initial_node,
      customColor: 'green',
    };

    return node;
  }
}
