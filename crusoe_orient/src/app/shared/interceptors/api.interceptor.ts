import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable } from 'rxjs';
import { OAuthService } from 'angular-oauth2-oidc';
import { environment } from 'src/environments/environment';

@Injectable()
export class ApiInterceptor implements HttpInterceptor {
  constructor(private oauthService: OAuthService) {}

  private needsAuth(url: string): boolean {
    return url.startsWith(environment.baseUrl)       
        || url.startsWith(environment.graphqlApi)    
        || url.startsWith(environment.tmpActApi)    
        || url.startsWith(environment.firewallApi);  
  }

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    let cloned = req;

    if (this.needsAuth(req.url)) {
      const token = this.oauthService.getAccessToken();
      if (token) {
        cloned = req.clone({
          setHeaders: { Authorization: `Bearer ${token}` },
        });
      }
    }

    return next.handle(cloned);
  }
}
