enabled = true;
bind_socket = "*:11332";
milter = true;
timeout = 120s;
upstream "local" {
  default = yes;
  self_scan = yes;
}
