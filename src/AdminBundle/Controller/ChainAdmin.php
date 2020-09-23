<?php


namespace AdminBundle\Controller;


use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use ThoughtBundle\Entity\Chain;

class ChainAdmin extends AbstractAdmin
{
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->add('name')
            ->add('_action', 'actions', [
                'actions' => [
                    'delete' => [],
                ],
            ])
        ;
    }

    public function toString($object)
    {
        return $object instanceof Chain
            ? $object->getName()
            : 'Chain';
    }
}