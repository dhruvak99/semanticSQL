import { AppBar, Box, Chip, Toolbar, Typography } from '@mui/material';

type HeaderProps = {
  drawerWidth: number;
};

export function Header({ drawerWidth }: HeaderProps) {
  return (
    <AppBar
      color="inherit"
      elevation={0}
      position="fixed"
      sx={{
        width: { md: `calc(100% - ${drawerWidth}px)` },
        ml: { md: `${drawerWidth}px` },
        borderBottom: '1px solid',
        borderColor: 'divider'
      }}
    >
      <Toolbar sx={{ gap: 2 }}>
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Typography variant="h6" noWrap>
            SemanticSQL
          </Typography>
        </Box>
        <Chip color="success" label="Production Analytics" size="small" variant="outlined" />
      </Toolbar>
    </AppBar>
  );
}
