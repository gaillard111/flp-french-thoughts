<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 26.11.18
 * Time: 11:21
 */

namespace AdminBundle\Controller;

use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use ThoughtBundle\Entity\Topic;

class TopicAdmin extends AbstractAdmin
{
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('name');
    }

    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->add('name')
            ->add('_action', 'actions', [
                'actions' => [
                    'edit'   => [],
                    'delete' => [],
                ],
            ])
        ;
    }

    public function toString($object)
    {
        return $object instanceof Topic
            ? $object->getName()
            : 'Topic';
    }
}