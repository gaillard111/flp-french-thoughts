<?php


namespace AdminBundle\EventListener;

use Sonata\AdminBundle\Event\ConfigureMenuEvent;
use Symfony\Component\Security\Core\Authorization\AuthorizationCheckerInterface;

/**
 * Class MenuBuilderListener
 * @package AdminBundle\EventListener
 */
class MenuBuilderListener
{
    protected $authorizationChecker;

    public function __construct(AuthorizationCheckerInterface $authorizationChecker)
    {
        $this->authorizationChecker = $authorizationChecker;
    }

    /**
     * @param ConfigureMenuEvent $event
     */
    public function adminMenuItems(ConfigureMenuEvent $event)
    {
        if ($this->authorizationChecker->isGranted('ROLE_ADMIN')) {
            $event->getMenu()
                ->removeChild('sonata_user')
                ->addChild(
                    '1',
                    [
                        'route' => 'admin_sonata_user_user_list',
                    ]
                )
                ->setExtras(
                    [
                        'icon' => '<span class="fa fa-users"></span>&nbsp;',
                    ]
                )
                ->setLabel('Users')
                ->getParent()
                ->addChild(
                    '2',
                    [
                        'route' => 'sonata_admin_custompage',
                    ]
                )
                ->setExtras(
                    [
                        'icon' => '<span class="fa fa-indent"></span>&nbsp;',
                    ]
                )
                ->setLabel('Import citation')
                ->getParent()
                ->addChild(
                    '3',
                    [
                        'route' => 'sonata_admin_author_import',
                    ]
                )
                ->setExtras(
                    [
                        'icon' => '<span class="fa fa-indent"></span>&nbsp;',
                    ]
                )
                ->setLabel('Import authors')
            ;
        }
    }
}