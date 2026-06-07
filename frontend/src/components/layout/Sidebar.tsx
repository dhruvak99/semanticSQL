import { Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from '@mui/material';
import { NavLink } from 'react-router-dom';
import { routes } from '../../config/routes';

type SidebarProps = {
  drawerWidth: number;
};

export function Sidebar({ drawerWidth }: SidebarProps) {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        display: { xs: 'none', md: 'block' },
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          borderRight: 0,
          color: '#dbeafe',
          background: 'linear-gradient(180deg, #061427 0%, #071c34 54%, #03111f 100%)'
        }
      }}
    >
      <Toolbar>
        <Box>
          <Typography variant="h6">SemanticSQL</Typography>
          <Typography sx={{ color: '#9fb2cc' }} variant="body2">
            Natural language RDBMS
          </Typography>
        </Box>
      </Toolbar>
      <List sx={{ px: 1 }}>
        {routes.map((route) => {
          const Icon = route.icon;

          return (
            <ListItemButton
              key={route.path}
              component={NavLink}
              to={route.path}
              end={route.path === '/'}
              sx={{
                borderRadius: 1,
                mb: 0.5,
                '&.active': {
                  bgcolor: '#3b4df5',
                  color: '#ffffff',
                  '& .MuiListItemIcon-root': {
                    color: '#ffffff'
                  }
                },
                '& .MuiListItemIcon-root': {
                  color: '#dbeafe'
                },
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.09)'
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <Icon fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={route.label}
                primaryTypographyProps={{ fontSize: 14, fontWeight: 700 }}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Drawer>
  );
}
